#!/usr/bin/env python3
"""
Portainer Management Tool

A comprehensive CLI tool for managing Portainer deployments on local network servers.
Provides intuitive commands for container, image, stack, network, and volume management.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import requests
import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
import questionary

# Load environment variables
load_dotenv()

console = Console()

class PortainerClient:
    """Client for interacting with Portainer API"""

    def __init__(self, url: Optional[str] = None, access_token: Optional[str] = None,
                 username: Optional[str] = None, password: Optional[str] = None):
        self.url = url or os.getenv('PORTAINER_URL', 'http://localhost:9000')

        # Priority: 1. Access token, 2. JWT token, 3. Username/password
        self.access_token = access_token or os.getenv('PORTAINER_ACCESS_TOKEN')
        self.jwt_token = os.getenv('PORTAINER_JWT_TOKEN')  # For direct JWT token usage
        self.username = username or os.getenv('PORTAINER_USERNAME')
        self.password = password or os.getenv('PORTAINER_PASSWORD')

        self.token_type = None  # 'access_token' or 'jwt'
        self.endpoint_id = None

        # Remove trailing slash from URL
        self.url = self.url.rstrip('/')

        # Authenticate on initialization
        if self.access_token:
            self.token_type = 'access_token'
            console.print("✅ Using API access token for authentication", style="green")
            self._get_default_endpoint()
        elif self.jwt_token:
            self.token_type = 'jwt'
            console.print("✅ Using JWT token for authentication", style="green")
            self._get_default_endpoint()
        elif self.username and self.password:
            self.authenticate()
        else:
            console.print("❌ No authentication credentials provided", style="red")
            console.print("💡 Set PORTAINER_ACCESS_TOKEN or PORTAINER_USERNAME/PASSWORD in .env", style="yellow")
            sys.exit(1)

    def authenticate(self):
        """Authenticate with Portainer and get JWT token from username/password"""
        try:
            response = requests.post(
                f"{self.url}/api/auth",
                json={"username": self.username, "password": self.password}
            )
            response.raise_for_status()
            data = response.json()
            self.jwt_token = data['jwt']
            self.token_type = 'jwt'

            # Get default endpoint
            self._get_default_endpoint()

            console.print("✅ Successfully authenticated with Portainer (JWT token - 8 hour validity)", style="green")
            console.print("💡 Consider using an API access token for long-term access", style="yellow")
        except requests.exceptions.RequestException as e:
            console.print(f"❌ Authentication failed: {e}", style="red")
            sys.exit(1)

    def _get_default_endpoint(self):
        """Get the default Docker endpoint ID"""
        headers = self._get_headers()
        response = requests.get(f"{self.url}/api/endpoints", headers=headers)
        response.raise_for_status()
        endpoints = response.json()

        if endpoints:
            # Use first available endpoint (usually local Docker)
            self.endpoint_id = endpoints[0]['Id']
        else:
            console.print("❌ No Docker endpoints found in Portainer", style="red")
            sys.exit(1)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        if self.token_type == 'access_token':
            if not self.access_token:
                raise ValueError("No access token available")
            return {"X-API-Key": self.access_token}
        elif self.token_type == 'jwt':
            if not self.jwt_token:
                raise ValueError("No JWT token available. Please authenticate first.")
            return {"Authorization": f"Bearer {self.jwt_token}"}
        else:
            raise ValueError("Not authenticated. Please provide credentials.")

    # Container Management Methods

    def list_containers(self, all: bool = False) -> List[Dict]:
        """List all containers"""
        headers = self._get_headers()
        params = {"all": "true" if all else "false"}
        response = requests.get(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/containers/json",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def create_container(self, image: str, name: str, ports: Optional[Dict] = None,
                        env: Optional[List[str]] = None, volumes: Optional[Dict] = None) -> Dict:
        """Create and start a new container"""
        headers = self._get_headers()

        # Container configuration
        config = {
            "Image": image,
            "Hostname": name,
            "ExposedPorts": {},
            "HostConfig": {
                "PortBindings": {},
                "Binds": [],
                "RestartPolicy": {"Name": "unless-stopped"}
            }
        }

        # Add port mappings
        if ports:
            for container_port, host_port in ports.items():
                config["ExposedPorts"][f"{container_port}/tcp"] = {}
                config["HostConfig"]["PortBindings"][f"{container_port}/tcp"] = [
                    {"HostPort": str(host_port)}
                ]

        # Add environment variables
        if env:
            config["Env"] = env

        # Add volume mounts
        if volumes:
            for host_path, container_path in volumes.items():
                config["HostConfig"]["Binds"].append(f"{host_path}:{container_path}")

        # Create container
        response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/containers/create",
            headers=headers,
            params={"name": name},
            json=config
        )
        response.raise_for_status()
        container_id = response.json()["Id"]

        # Start container
        start_response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/containers/{container_id}/start",
            headers=headers
        )
        start_response.raise_for_status()

        return {"Id": container_id, "Name": name}

    def stop_container(self, container_id: str):
        """Stop a running container"""
        headers = self._get_headers()
        response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/containers/{container_id}/stop",
            headers=headers
        )
        response.raise_for_status()

    def start_container(self, container_id: str):
        """Start a stopped container"""
        headers = self._get_headers()
        response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/containers/{container_id}/start",
            headers=headers
        )
        response.raise_for_status()

    def restart_container(self, container_id: str):
        """Restart a container"""
        headers = self._get_headers()
        response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/containers/{container_id}/restart",
            headers=headers
        )
        response.raise_for_status()

    def remove_container(self, container_id: str, force: bool = False):
        """Remove a container"""
        headers = self._get_headers()
        params = {"force": "true" if force else "false"}
        response = requests.delete(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/containers/{container_id}",
            headers=headers,
            params=params
        )
        response.raise_for_status()

    def get_container_logs(self, container_id: str, tail: int = 100, follow: bool = False) -> str:
        """Get container logs"""
        headers = self._get_headers()
        params = {
            "stdout": "true",
            "stderr": "true",
            "tail": str(tail),
            "follow": "true" if follow else "false"
        }
        response = requests.get(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/containers/{container_id}/logs",
            headers=headers,
            params=params,
            stream=follow
        )
        response.raise_for_status()

        if follow:
            # Stream logs
            for line in response.iter_lines():
                if line:
                    yield line.decode('utf-8')
        else:
            return response.text

    def exec_container(self, container_id: str, command: List[str]) -> str:
        """Execute command in container"""
        headers = self._get_headers()

        # Create exec instance
        exec_config = {
            "AttachStdout": True,
            "AttachStderr": True,
            "Cmd": command
        }
        exec_response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/containers/{container_id}/exec",
            headers=headers,
            json=exec_config
        )
        exec_response.raise_for_status()
        exec_id = exec_response.json()["Id"]

        # Start exec
        start_response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/exec/{exec_id}/start",
            headers=headers,
            json={"Detach": False, "Tty": False}
        )
        start_response.raise_for_status()

        return start_response.text

    # Image Management Methods

    def list_images(self) -> List[Dict]:
        """List all Docker images"""
        headers = self._get_headers()
        response = requests.get(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/images/json",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def pull_image(self, image_name: str):
        """Pull image from registry"""
        headers = self._get_headers()
        params = {"fromImage": image_name}
        response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/images/create",
            headers=headers,
            params=params
        )
        response.raise_for_status()

    def remove_image(self, image_id: str, force: bool = False):
        """Remove a Docker image"""
        headers = self._get_headers()
        params = {"force": "true" if force else "false"}
        response = requests.delete(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/images/{image_id}",
            headers=headers,
            params=params
        )
        response.raise_for_status()

    def build_image(self, dockerfile_path: str, tag: str) -> bool:
        """Build Docker image from Dockerfile"""
        headers = self._get_headers()

        # This requires sending tar archive of build context
        # For simplicity, we'll document this as requiring docker CLI locally
        console.print("🔨 Building image locally (requires Docker CLI)...", style="yellow")
        import subprocess

        result = subprocess.run(
            ["docker", "build", "-t", tag, os.path.dirname(dockerfile_path)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            console.print(f"✅ Successfully built image: {tag}", style="green")
            # TODO: Push to Portainer registry if configured
            return True
        else:
            console.print(f"❌ Build failed: {result.stderr}", style="red")
            return False

    # Stack Management Methods

    def list_stacks(self) -> List[Dict]:
        """List all stacks"""
        headers = self._get_headers()
        response = requests.get(
            f"{self.url}/api/stacks",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def deploy_stack(self, name: str, compose_file: str, env_vars: Optional[Dict] = None):
        """Deploy a stack from docker-compose file"""
        headers = self._get_headers()

        with open(compose_file, 'r') as f:
            compose_content = f.read()

        stack_data = {
            "Name": name,
            "StackFileContent": compose_content,
            "Env": [{"name": k, "value": v} for k, v in (env_vars or {}).items()]
        }

        response = requests.post(
            f"{self.url}/api/stacks",
            headers=headers,
            params={"endpointId": self.endpoint_id, "type": 2},  # type 2 = compose stack
            json=stack_data
        )
        response.raise_for_status()
        return response.json()

    def remove_stack(self, stack_id: int):
        """Remove a stack"""
        headers = self._get_headers()
        response = requests.delete(
            f"{self.url}/api/stacks/{stack_id}",
            headers=headers,
            params={"endpointId": self.endpoint_id}
        )
        response.raise_for_status()

    # Network Management Methods

    def list_networks(self) -> List[Dict]:
        """List all Docker networks"""
        headers = self._get_headers()
        response = requests.get(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/networks",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def create_network(self, name: str, driver: str = "bridge") -> Dict:
        """Create a Docker network"""
        headers = self._get_headers()
        network_config = {
            "Name": name,
            "Driver": driver,
            "CheckDuplicate": True
        }
        response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/networks/create",
            headers=headers,
            json=network_config
        )
        response.raise_for_status()
        return response.json()

    # Volume Management Methods

    def list_volumes(self) -> List[Dict]:
        """List all Docker volumes"""
        headers = self._get_headers()
        response = requests.get(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/volumes",
            headers=headers
        )
        response.raise_for_status()
        return response.json()["Volumes"]

    def create_volume(self, name: str, driver: str = "local") -> Dict:
        """Create a Docker volume"""
        headers = self._get_headers()
        volume_config = {
            "Name": name,
            "Driver": driver
        }
        response = requests.post(
            f"{self.url}/api/endpoints/{self.endpoint_id}/docker/volumes/create",
            headers=headers,
            json=volume_config
        )
        response.raise_for_status()
        return response.json()


# CLI Command Functions

def cmd_deploy(client: PortainerClient, args):
    """Deploy a container from an image"""
    console.print(f"🚀 Deploying container from image: {args.image}")

    # Parse port mappings
    ports = {}
    if args.port:
        for port_map in args.port:
            if ':' in port_map:
                host_port, container_port = port_map.split(':')
                ports[container_port] = host_port
            else:
                ports[port_map] = port_map

    # Parse environment variables
    env = args.env if args.env else []

    # Parse volume mounts
    volumes = {}
    if args.volume:
        for vol_map in args.volume:
            if ':' in vol_map:
                host_path, container_path = vol_map.split(':', 1)
                volumes[host_path] = container_path

    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Creating container...", total=None)

            # Pull image if needed
            if args.pull:
                progress.update(task, description="Pulling image...")
                client.pull_image(args.image)

            progress.update(task, description="Creating and starting container...")
            result = client.create_container(
                image=args.image,
                name=args.name,
                ports=ports,
                env=env,
                volumes=volumes
            )

        console.print(f"✅ Container '{args.name}' deployed successfully!", style="green")
        console.print(f"Container ID: {result['Id'][:12]}")

        if ports:
            console.print("\n📡 Port mappings:")
            for container_port, host_port in ports.items():
                console.print(f"  - {host_port} → {container_port}")

    except Exception as e:
        console.print(f"❌ Failed to deploy container: {e}", style="red")
        sys.exit(1)

def cmd_list(client: PortainerClient, args):
    """List containers"""
    containers = client.list_containers(all=args.all)

    if not containers:
        console.print("No containers found", style="yellow")
        return

    table = Table(title="Docker Containers")
    table.add_column("Name", style="cyan")
    table.add_column("Image", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Ports", style="yellow")
    table.add_column("ID", style="dim")

    for container in containers:
        name = container['Names'][0].lstrip('/') if container['Names'] else 'N/A'
        image = container['Image']
        status = container['Status'] if 'Status' in container else container['State']

        # Format ports
        ports = []
        for port in container.get('Ports', []):
            if 'PublicPort' in port:
                ports.append(f"{port['PublicPort']}→{port['PrivatePort']}")
            else:
                ports.append(str(port['PrivatePort']))
        ports_str = ', '.join(ports) if ports else 'None'

        container_id = container['Id'][:12]

        table.add_row(name, image, status, ports_str, container_id)

    console.print(table)

def cmd_stop(client: PortainerClient, args):
    """Stop a container"""
    console.print(f"🛑 Stopping container: {args.container}")
    try:
        client.stop_container(args.container)
        console.print(f"✅ Container stopped successfully", style="green")
    except Exception as e:
        console.print(f"❌ Failed to stop container: {e}", style="red")
        sys.exit(1)

def cmd_start(client: PortainerClient, args):
    """Start a container"""
    console.print(f"▶️ Starting container: {args.container}")
    try:
        client.start_container(args.container)
        console.print(f"✅ Container started successfully", style="green")
    except Exception as e:
        console.print(f"❌ Failed to start container: {e}", style="red")
        sys.exit(1)

def cmd_restart(client: PortainerClient, args):
    """Restart a container"""
    console.print(f"🔄 Restarting container: {args.container}")
    try:
        client.restart_container(args.container)
        console.print(f"✅ Container restarted successfully", style="green")
    except Exception as e:
        console.print(f"❌ Failed to restart container: {e}", style="red")
        sys.exit(1)

def cmd_remove(client: PortainerClient, args):
    """Remove a container"""
    if not args.force:
        confirm = Confirm.ask(f"Are you sure you want to remove container '{args.container}'?")
        if not confirm:
            console.print("Cancelled", style="yellow")
            return

    console.print(f"🗑️ Removing container: {args.container}")
    try:
        client.remove_container(args.container, force=args.force)
        console.print(f"✅ Container removed successfully", style="green")
    except Exception as e:
        console.print(f"❌ Failed to remove container: {e}", style="red")
        sys.exit(1)

def cmd_logs(client: PortainerClient, args):
    """View container logs"""
    try:
        if args.follow:
            console.print(f"📜 Following logs for container: {args.container} (Ctrl+C to stop)")
            for line in client.get_container_logs(args.container, tail=args.tail, follow=True):
                console.print(line)
        else:
            logs = client.get_container_logs(args.container, tail=args.tail, follow=False)
            console.print(Panel(logs, title=f"Logs from {args.container}", expand=False))
    except KeyboardInterrupt:
        console.print("\n👋 Stopped following logs", style="yellow")
    except Exception as e:
        console.print(f"❌ Failed to get logs: {e}", style="red")
        sys.exit(1)

def cmd_exec(client: PortainerClient, args):
    """Execute command in container"""
    console.print(f"🖥️ Executing command in container: {args.container}")
    console.print(f"Command: {' '.join(args.command)}", style="dim")

    try:
        output = client.exec_container(args.container, args.command)
        console.print("\nOutput:")
        console.print(output)
    except Exception as e:
        console.print(f"❌ Failed to execute command: {e}", style="red")
        sys.exit(1)

def cmd_images(client: PortainerClient, args):
    """List Docker images"""
    images = client.list_images()

    if not images:
        console.print("No images found", style="yellow")
        return

    table = Table(title="Docker Images")
    table.add_column("Repository", style="cyan")
    table.add_column("Tag", style="magenta")
    table.add_column("Size", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("ID", style="dim")

    for image in images:
        repo_tags = image.get('RepoTags', ['<none>:<none>'])
        for repo_tag in repo_tags:
            if ':' in repo_tag:
                repo, tag = repo_tag.rsplit(':', 1)
            else:
                repo, tag = repo_tag, 'latest'

            size_mb = image['Size'] / (1024 * 1024)
            created = datetime.fromtimestamp(image['Created']).strftime('%Y-%m-%d %H:%M')
            image_id = image['Id'].split(':')[1][:12] if ':' in image['Id'] else image['Id'][:12]

            table.add_row(repo, tag, f"{size_mb:.1f} MB", created, image_id)

    console.print(table)

def cmd_pull(client: PortainerClient, args):
    """Pull image from registry"""
    console.print(f"⬇️ Pulling image: {args.image}")

    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(f"Pulling {args.image}...", total=None)
            client.pull_image(args.image)

        console.print(f"✅ Image pulled successfully", style="green")
    except Exception as e:
        console.print(f"❌ Failed to pull image: {e}", style="red")
        sys.exit(1)

def cmd_build(client: PortainerClient, args):
    """Build Docker image"""
    dockerfile_path = args.path or './Dockerfile'

    if not os.path.exists(dockerfile_path):
        console.print(f"❌ Dockerfile not found: {dockerfile_path}", style="red")
        sys.exit(1)

    console.print(f"🔨 Building image from: {dockerfile_path}")
    console.print(f"Tag: {args.tag}")

    success = client.build_image(dockerfile_path, args.tag)

    if success and args.deploy:
        console.print("\n🚀 Deploying built image...")
        name = args.tag.split(':')[0].split('/')[-1]  # Extract name from tag
        client.create_container(
            image=args.tag,
            name=f"{name}-{int(time.time())}"
        )
        console.print(f"✅ Container deployed from built image", style="green")

def cmd_stack_deploy(client: PortainerClient, args):
    """Deploy a stack from docker-compose file"""
    if not os.path.exists(args.file):
        console.print(f"❌ Compose file not found: {args.file}", style="red")
        sys.exit(1)

    console.print(f"🚀 Deploying stack: {args.name}")
    console.print(f"Compose file: {args.file}")

    # Parse environment variables
    env_vars = {}
    if args.env:
        for env_pair in args.env:
            if '=' in env_pair:
                key, value = env_pair.split('=', 1)
                env_vars[key] = value

    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Deploying stack...", total=None)
            result = client.deploy_stack(args.name, args.file, env_vars)

        console.print(f"✅ Stack '{args.name}' deployed successfully!", style="green")
        console.print(f"Stack ID: {result.get('Id', 'N/A')}")
    except Exception as e:
        console.print(f"❌ Failed to deploy stack: {e}", style="red")
        sys.exit(1)

def cmd_stack_list(client: PortainerClient, args):
    """List all stacks"""
    stacks = client.list_stacks()

    if not stacks:
        console.print("No stacks found", style="yellow")
        return

    table = Table(title="Portainer Stacks")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("ID", style="dim")

    for stack in stacks:
        stack_type = "Compose" if stack.get('Type') == 2 else "Swarm"
        status = stack.get('Status', 'Active')
        created = stack.get('CreationDate', 'N/A')

        table.add_row(
            stack['Name'],
            stack_type,
            str(status),
            created,
            str(stack['Id'])
        )

    console.print(table)

def cmd_stack_remove(client: PortainerClient, args):
    """Remove a stack"""
    if not args.force:
        confirm = Confirm.ask(f"Are you sure you want to remove stack '{args.name}'?")
        if not confirm:
            console.print("Cancelled", style="yellow")
            return

    # Find stack ID by name
    stacks = client.list_stacks()
    stack_id = None
    for stack in stacks:
        if stack['Name'] == args.name:
            stack_id = stack['Id']
            break

    if not stack_id:
        console.print(f"❌ Stack '{args.name}' not found", style="red")
        sys.exit(1)

    console.print(f"🗑️ Removing stack: {args.name}")
    try:
        client.remove_stack(stack_id)
        console.print(f"✅ Stack removed successfully", style="green")
    except Exception as e:
        console.print(f"❌ Failed to remove stack: {e}", style="red")
        sys.exit(1)

def cmd_network_list(client: PortainerClient, args):
    """List Docker networks"""
    networks = client.list_networks()

    if not networks:
        console.print("No networks found", style="yellow")
        return

    table = Table(title="Docker Networks")
    table.add_column("Name", style="cyan")
    table.add_column("Driver", style="magenta")
    table.add_column("Scope", style="green")
    table.add_column("ID", style="dim")

    for network in networks:
        table.add_row(
            network['Name'],
            network['Driver'],
            network.get('Scope', 'N/A'),
            network['Id'][:12]
        )

    console.print(table)

def cmd_network_create(client: PortainerClient, args):
    """Create a Docker network"""
    console.print(f"🌐 Creating network: {args.name}")

    try:
        result = client.create_network(args.name, driver=args.driver)
        console.print(f"✅ Network created successfully", style="green")
        console.print(f"Network ID: {result['Id'][:12]}")
    except Exception as e:
        console.print(f"❌ Failed to create network: {e}", style="red")
        sys.exit(1)

def cmd_volume_list(client: PortainerClient, args):
    """List Docker volumes"""
    volumes = client.list_volumes()

    if not volumes:
        console.print("No volumes found", style="yellow")
        return

    table = Table(title="Docker Volumes")
    table.add_column("Name", style="cyan")
    table.add_column("Driver", style="magenta")
    table.add_column("Mount Point", style="green")

    for volume in volumes:
        table.add_row(
            volume['Name'],
            volume['Driver'],
            volume.get('Mountpoint', 'N/A')
        )

    console.print(table)

def cmd_volume_create(client: PortainerClient, args):
    """Create a Docker volume"""
    console.print(f"💾 Creating volume: {args.name}")

    try:
        result = client.create_volume(args.name, driver=args.driver)
        console.print(f"✅ Volume created successfully", style="green")
        console.print(f"Volume name: {result['Name']}")
    except Exception as e:
        console.print(f"❌ Failed to create volume: {e}", style="red")
        sys.exit(1)

def cmd_config(client: PortainerClient, args):
    """Show or update Portainer configuration"""
    if args.set:
        # Update configuration
        key, value = args.set.split('=', 1)

        # Create or update .env file
        env_path = Path('.env')
        env_vars = {}

        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        k, v = line.strip().split('=', 1)
                        env_vars[k] = v

        # Update the specific key
        env_key = f"PORTAINER_{key.upper()}"
        env_vars[env_key] = value

        # Write back to .env
        with open(env_path, 'w') as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")

        console.print(f"✅ Updated {env_key} in .env file", style="green")
    else:
        # Show current configuration
        config_table = Table(title="Portainer Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="magenta")

        config_table.add_row("URL", client.url)
        config_table.add_row("Auth Type", client.token_type or "Not authenticated")
        if client.token_type == 'access_token':
            config_table.add_row("Access Token", f"{client.access_token[:20]}..." if client.access_token else "Not set")
        elif client.token_type == 'jwt':
            config_table.add_row("Username", client.username or "N/A")
            config_table.add_row("JWT Token", "Active (8hr validity)" if client.jwt_token else "Not set")
        else:
            config_table.add_row("Username", client.username or "Not set")
            config_table.add_row("Password", "***" if client.password else "Not set")
        config_table.add_row("Endpoint ID", str(client.endpoint_id) if client.endpoint_id else "Not set")

        console.print(config_table)

def main():
    parser = argparse.ArgumentParser(
        description="Portainer Management Tool - Manage containers, images, and stacks on your local network server",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Global options
    parser.add_argument('--url', help='Portainer server URL')
    parser.add_argument('--token', help='Portainer API access token (recommended)')
    parser.add_argument('--username', help='Portainer username (for JWT auth)')
    parser.add_argument('--password', help='Portainer password (for JWT auth)')

    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # Container management commands
    deploy_parser = subparsers.add_parser('deploy', help='Deploy a new container')
    deploy_parser.add_argument('image', help='Docker image to deploy')
    deploy_parser.add_argument('--name', required=True, help='Container name')
    deploy_parser.add_argument('-p', '--port', action='append', help='Port mapping (e.g., 8080:80)')
    deploy_parser.add_argument('-e', '--env', action='append', help='Environment variable (e.g., KEY=value)')
    deploy_parser.add_argument('-v', '--volume', action='append', help='Volume mount (e.g., /host/path:/container/path)')
    deploy_parser.add_argument('--pull', action='store_true', help='Pull image before deploying')

    list_parser = subparsers.add_parser('list', help='List containers')
    list_parser.add_argument('-a', '--all', action='store_true', help='Show all containers (including stopped)')

    stop_parser = subparsers.add_parser('stop', help='Stop a container')
    stop_parser.add_argument('container', help='Container name or ID')

    start_parser = subparsers.add_parser('start', help='Start a container')
    start_parser.add_argument('container', help='Container name or ID')

    restart_parser = subparsers.add_parser('restart', help='Restart a container')
    restart_parser.add_argument('container', help='Container name or ID')

    remove_parser = subparsers.add_parser('remove', help='Remove a container')
    remove_parser.add_argument('container', help='Container name or ID')
    remove_parser.add_argument('-f', '--force', action='store_true', help='Force removal')

    logs_parser = subparsers.add_parser('logs', help='View container logs')
    logs_parser.add_argument('container', help='Container name or ID')
    logs_parser.add_argument('--tail', type=int, default=100, help='Number of lines to show (default: 100)')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='Follow log output')

    exec_parser = subparsers.add_parser('exec', help='Execute command in container')
    exec_parser.add_argument('container', help='Container name or ID')
    exec_parser.add_argument('command', nargs='+', help='Command to execute')

    # Image management commands
    images_parser = subparsers.add_parser('images', help='List Docker images')

    pull_parser = subparsers.add_parser('pull', help='Pull image from registry')
    pull_parser.add_argument('image', help='Image name to pull')

    build_parser = subparsers.add_parser('build', help='Build Docker image from Dockerfile')
    build_parser.add_argument('--tag', '-t', required=True, help='Image tag')
    build_parser.add_argument('--path', help='Path to Dockerfile directory (default: current directory)')
    build_parser.add_argument('--deploy', action='store_true', help='Deploy container after building')

    # Stack management commands
    stack_deploy_parser = subparsers.add_parser('stack-deploy', help='Deploy a stack from docker-compose')
    stack_deploy_parser.add_argument('--name', '-n', required=True, help='Stack name')
    stack_deploy_parser.add_argument('--file', '-f', default='docker-compose.yml', help='Compose file path')
    stack_deploy_parser.add_argument('-e', '--env', action='append', help='Environment variable (KEY=value)')

    stack_list_parser = subparsers.add_parser('stack-list', help='List deployed stacks')

    stack_remove_parser = subparsers.add_parser('stack-remove', help='Remove a stack')
    stack_remove_parser.add_argument('name', help='Stack name')
    stack_remove_parser.add_argument('-f', '--force', action='store_true', help='Force removal')

    # Network management commands
    network_list_parser = subparsers.add_parser('network-list', help='List Docker networks')

    network_create_parser = subparsers.add_parser('network-create', help='Create a Docker network')
    network_create_parser.add_argument('name', help='Network name')
    network_create_parser.add_argument('--driver', default='bridge', help='Network driver (default: bridge)')

    # Volume management commands
    volume_list_parser = subparsers.add_parser('volume-list', help='List Docker volumes')

    volume_create_parser = subparsers.add_parser('volume-create', help='Create a Docker volume')
    volume_create_parser.add_argument('name', help='Volume name')
    volume_create_parser.add_argument('--driver', default='local', help='Volume driver (default: local)')

    # Configuration command
    config_parser = subparsers.add_parser('config', help='Show or update configuration')
    config_parser.add_argument('--set', help='Set configuration value (e.g., url=http://localhost:9000)')

    args = parser.parse_args()

    # Initialize Portainer client
    try:
        client = PortainerClient(
            url=args.url if hasattr(args, 'url') and args.url else None,
            access_token=args.token if hasattr(args, 'token') and args.token else None,
            username=args.username if hasattr(args, 'username') and args.username else None,
            password=args.password if hasattr(args, 'password') and args.password else None
        )
    except Exception as e:
        console.print(f"❌ Failed to initialize Portainer client: {e}", style="red")
        console.print("\n💡 Tip: Set PORTAINER_ACCESS_TOKEN (recommended) or PORTAINER_USERNAME/PASSWORD in your .env file", style="yellow")
        console.print("To get an access token: Login to Portainer → My Account → Access tokens → Add access token", style="yellow")
        sys.exit(1)

    # Execute command
    command_map = {
        'deploy': cmd_deploy,
        'list': cmd_list,
        'stop': cmd_stop,
        'start': cmd_start,
        'restart': cmd_restart,
        'remove': cmd_remove,
        'logs': cmd_logs,
        'exec': cmd_exec,
        'images': cmd_images,
        'pull': cmd_pull,
        'build': cmd_build,
        'stack-deploy': cmd_stack_deploy,
        'stack-list': cmd_stack_list,
        'stack-remove': cmd_stack_remove,
        'network-list': cmd_network_list,
        'network-create': cmd_network_create,
        'volume-list': cmd_volume_list,
        'volume-create': cmd_volume_create,
        'config': cmd_config,
    }

    if args.command in command_map:
        command_map[args.command](client, args)
    else:
        console.print(f"❌ Unknown command: {args.command}", style="red")
        sys.exit(1)

if __name__ == "__main__":
    main()
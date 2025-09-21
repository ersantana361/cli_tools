# LeetCode 102: Binary Tree Level Order Traversal

**Difficulty:** Medium
**Topics:** Tree, Breadth-First Search, Binary Tree

## Problem Description

Given the `root` of a binary tree, return *the level order traversal of its nodes' values*. (i.e., from left to right, level by level).**Example 1:**![Image](https://assets.leetcode.com/uploads/2021/02/19/tree1.jpg)**Input:** root = [3,9,20,null,null,15,7] **Output:** [[3],[9,20],[15,7]]**Example 2:**

**Input:** root = [1] **Output:** [[1]]**Example 3:**

**Input:** root = [] **Output:** []**Constraints:**- The number of nodes in the tree is in the range `[0, 2000]`.- `-1000 <= Node.val <= 1000`

## Examples

**Example 1:**![Image](https://assets.leetcode.com/uploads/2021/02/19/tree1.jpg)**Input:** root = [3,9,20,null,null,15,7]
**Output:** [[3],[9,20],[15,7]]


**Example 2:** **Input:** root = [1]
**Output:** [[1]]


**Example 3:** **Input:** root = []
**Output:** []


## Constraints

**- The number of nodes in the tree is in the range `[0, 2000]`.- `-1000 <= Node.val <= 1000`

## Editorial

*Note: This is extracted from the saved HTML page. The full editorial content*
*would typically be loaded separately via API calls.*

### Approach

Based on the problem (Binary Tree Level Order Traversal), the standard approaches are:

1. **BFS (Breadth-First Search) with Queue**
   - Use a queue to traverse level by level
   - For each level, process all nodes currently in the queue
   - Add children to the queue for the next level

2. **DFS (Depth-First Search) with Level Tracking**
   - Use recursion with level parameter
   - Group nodes by their depth level

### Implementation Notes

- Time Complexity: O(n) where n is the number of nodes
- Space Complexity: O(w) where w is the maximum width of the tree

### Code Template

```python
# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right

class Solution:
    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        if not root:
            return []
        
        result = []
        queue = [root]
        
        while queue:
            level_size = len(queue)
            level_values = []
            
            for _ in range(level_size):
                node = queue.pop(0)
                level_values.append(node.val)
                
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
            
            result.append(level_values)
        
        return result
```

## Similar Questions

- [Binary Tree Zigzag Level Order Traversal] (Difficulty: Medium)
- [Binary Tree Level Order Traversal II] (Difficulty: Medium)
- [Minimum Depth of Binary Tree] (Difficulty: Easy)
- [Binary Tree Vertical Order Traversal] (Difficulty: Medium)
- [Average of Levels in Binary Tree] (Difficulty: Easy)

---
*Extracted from LeetCode on 1757978720.0464108*
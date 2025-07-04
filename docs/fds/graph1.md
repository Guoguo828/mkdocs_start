# 图1

## 基本概念

1. **节点，边**  
2. **有向图，无向图**  
3. **图的限制**  
   - 图是没有自环的。  
   - 每两个点之间只有一条边（多边的情况这里不考虑）。  
4. **路径，联通，连通图**  
5. **完全图**  
   - 每两个点之间都有边。  
6. **子图**  
   - 连通子图  
   - 最大连通子图  
7. **图上的树**  
   - 没有回路的连通图。  
8. **DAG（有向无环图）**  
9. **强连通图**  
   - 有向图中，每两个点之间都有边，且任意两点之间都存在一条有向路径。  
   - 弱连通图：忽略方向后是连通的图。  
10. **强连通分量**  
    - 图的其中一块，每两个点之间都有边，且任意两点之间都存在一条有向路径。  
    - 弱连通分量：忽略方向后是连通的子图。  
11. **度/出度和入度**  
    - **度**：一个点的度是该点与所有其他点的连边数。  
    - **入度**：指向该点的边数。  
    - **出度**：从该点出发的边数。

---

## 图的表示

我们发现，图最重要的就是表示两件事情：**边和点**。

1. **邻接矩阵**  
   - 一个二维数组 `a[i][j]`，有值表示 `i` 到 `j` 有边，没有值表示没有边。  
   - 缺点：这种表示方式会浪费很多空间，尤其是稀疏图。  

2. **邻接链表**  
   - 邻接表是一个数组，数组的每个元素是一个链表，链表中的每个元素是一个节点。  
   - 节点中包含：  
     - 一个指向下一个节点的指针。  
     - 一个指向另一个节点的指针。  
   - 每个链表节点代表的是从对应（链表头）点出去的边连接的点。  

   **问题**：如何找到指向某个点的节点？  
   - **解决方法 1**：使用反向链表，从对应点进来的边连接的点作为链表的节点。  
   - **解决方法 2**：使用多重链表（十字链表）。  

3. **多重链表（十字链表）（有向图）**  
   - 一个行的链表，一个列的链表。  
   - **行链表**：存储发出的点。  
   - **列链表**：存储进入的点。  
   - 每个节点包含：  
     - 两个图中的节点，分别代表出发点和到达点。  
     - 两个指针：  
       - 左指针：存储第一个点的下一个出发点所在的节点。  
       - 右指针：存储第二个点的下一个进入点所在的节点。
   - **优点**：可以快速找到指向某个点的节点。
   - **无向图也可以用**：把所有包含这个点的节点都放入这个点的链表，注意指针要是这个点管的指针（左 or 右）。

---

## 拓扑排序

1. **定义**  
   拓扑排序是有向无环图（DAG）的一种线性序列，使得对于每一条边 `(u, v)`，点 `u` 在点 `v` 之前。

2. **题意描述**  
   简单来说，比如选课问题：某些课程有先修要求，必须修完所有先修课才能修这门课。给出所有的先修要求，求一个合理的修课顺序。

3. **算法描述**  
   - 把每个课程看作一个点，先修课的要求看作一条边。  
   - 入度为 0 的点表示没有先修课或先修课已修完，可以直接修这门课。  
   - 初始时，将所有入度为 0 的点加入队列。  
   - 每次从队列中取出一个点，将其出度对应的点的入度减 1。  
   - 如果某个点的入度变为 0，则将其加入队列。  
   - 重复上述过程，直到队列为空，得到一个拓扑排序。

4. **拓扑排序的代码**  
   ![拓扑排序代码](topsort.jpg "拓扑排序")

   从代码中可以看出，拓扑排序利用了队列进行图的遍历搜索，这是一种**广度优先搜索（BFS）**的方式。  
   核心思想是：  
   - 初始队列，挑一个点入队。  
   - 出队，找这个点有关的点，入队。  
   - 重复这个过程，直到队列为空。

5. **复杂度分析**  
   - 时间复杂度：`O(V + E)`，其中 `V` 是点的个数，`E` 是边的个数。

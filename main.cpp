#include <iostream>
#include "Graph.hpp"

int main() {
    Graph<int> g;
    for(int i = 0; i < 10; i++) {
        Vertex<int> v(i);
        g.add_vertex(v);
    }

    for(int i = 0; i < 10; i++) {
        for(int j = i + 1; j < 10; j++) {
            g.add_edge(Edge<int>(i, j, 1.0));
            g.add_edge(Edge<int>(j, i, 1.0));
        }
    }

    std::cout << g << "\n";

    return 0;
}

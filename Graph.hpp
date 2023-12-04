#ifndef GRAPH_HPP
#define GRAPH_HPP

#include <functional>
#include <unordered_set>
#include <unordered_map>
#include "Vertex.hpp"
#include "Edge.hpp"

template<typename T>
struct Graph {
    std::unordered_set<Vertex<T>> vertices;
    std::unordered_multiset<Edge<T>> edges;
    std::unordered_map<Vertex<T>, std::unordered_multiset<Edge<T>>> adjacency_list;

    void add_vertex(const Vertex<T> &vertex) {
        vertices.insert(vertex);
    }

    void add_edge(const Edge<T> &edge) {
        edges.insert(edge);
        adjacency_list[edge.from].insert(edge);
    }

    std::vector<Edge<T>> get_edges_from(T vertexId) const {
        auto it = adjacency_list.find(vertexId);
        if (it != adjacency_list.end()) {
            return it->second;
        }
        return {};
    }

    friend std::ostream &operator<<(std::ostream &os, const Graph &graph) {
        os << "Graph(\n\tVertices: {\n";
        for(Vertex<T> vertex: graph.vertices) {
            os << "\t\t" << vertex << "\n";
        }
        os << "\t},\n\tEdges: {\n";
        for(Edge<T> edge: graph.edges) {
            os << "\t\t" << edge << "\n";
        }
        os << "\t}\n}";
        return os;
    }
};

#endif // GRAPH_HPP

#ifndef EDGE_HPP
#define EDGE_HPP

#include <iostream>
#include <functional>
#include "Utils.hpp"
#include "Vertex.hpp"

template<typename T>
struct Edge {
    Vertex<T> from;
    Vertex<T> to;
    double weight;

    Edge(T from_id, T to_id, double weight) : from(Vertex(from_id)), to(Vertex(to_id)), weight(weight) {}

    Edge(Vertex<T> from, Vertex<T> to, double weight) : from(from), to(to), weight(weight) {}

    bool operator==(const Edge &other) const {
        return from == other.from && to == other.to && weight == other.weight;
    }

    friend std::ostream &operator<<(std::ostream &os, const Edge &edge) {
        os << "Edge(From: " << edge.from << ", To: " << edge.to << ", Weight: " << edge.weight << ")";
        return os;
    }
};

namespace std {
    template<typename T>
    struct hash<Edge < T>> {
    size_t operator()(const Edge <T> &edge) const {
        size_t h = 0;
        hash_combine(h, std::hash<Vertex<T>>()(edge.from));
        hash_combine(h, std::hash<Vertex<T>>()(edge.to));
        hash_combine(h, std::hash<double>()(edge.weight));
        return h;
    }
};
}

#endif // EDGE_HPP

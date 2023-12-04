#ifndef VERTEX_HPP
#define VERTEX_HPP

#include <iostream>
#include <functional>
#include <utility>

template<typename T>
struct Vertex {
    T id;
    std::string label;

    explicit Vertex(T id) : id(id) { label = ""; }

    Vertex(T id, std::string label) : id(id), label(std::move(label)) {}

    bool operator==(const Vertex &other) const {
        return id == other.id;
    }

    friend std::ostream &operator<<(std::ostream &os, const Vertex &vertex) {
        os << "Vertex(ID: " << vertex.id;
        if (!vertex.label.empty()) {
            os << ", Label: " << vertex.label;
        }
        os << ")";
        return os;
    }
};

namespace std {
    template<typename T>
    struct hash<Vertex < T>> {
    size_t operator()(const Vertex <T> &vertex) const {
        return std::hash<T>()(vertex.id);
    }
};
}

#endif // VERTEX_HPP

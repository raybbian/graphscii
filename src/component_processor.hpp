#ifndef COMPONENT_PROCESSOR_HPP
#define COMPONENT_PROCESSOR_HPP

#include <boost/graph/connected_components.hpp>

struct ComponentProcessor {
    SimpleGraph input_graph;
    std::vector<int> component_map; //maps vertex to component_id
    std::vector<unsigned long> vertex_map; //maps vertex_id in input_graph to vertex_id in its component
    std::vector<SimpleGraph> components;

    ComponentProcessor(const SimpleGraph &input_graph) : input_graph(input_graph) {
        component_map = std::vector<int>(boost::num_vertices(input_graph));
        vertex_map = std::vector<unsigned long>(boost::num_vertices(input_graph));
    }

    void generate_connected_components() {
        int num_connected_components = boost::connected_components(input_graph, &component_map[0]);
        components = std::vector<SimpleGraph>(num_connected_components);
        auto vertex_it = boost::vertices(input_graph);
        for (auto it = vertex_it.first; it != vertex_it.second; it++) {
            vertex_map[*it] = boost::add_vertex(components[component_map[*it]]);
        }
        auto edge_it = boost::edges(input_graph);
        for (auto it = edge_it.first; it != edge_it.second; it++) {
            int component_id = component_map[boost::source(*it, input_graph)];
            unsigned long source_id = vertex_map[boost::source(*it, input_graph)];
            unsigned long target_id = vertex_map[boost::target(*it, input_graph)];
            boost::add_edge(source_id, target_id, components[component_id]);
        }
    }
};


#endif
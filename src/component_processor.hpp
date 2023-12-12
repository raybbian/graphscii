#ifndef COMPONENT_PROCESSOR_HPP
#define COMPONENT_PROCESSOR_HPP

#include <boost/graph/connected_components.hpp>

namespace ComponentProcessor {
    std::vector<simple_graph_t> generate_connected_components(const simple_graph_t &input_graph) {
        /* init mapping structures */
        auto component_map = std::vector<int>(boost::num_vertices(input_graph));
        auto vertex_map = std::vector<simple_graph_t::vertex_descriptor>(boost::num_vertices(input_graph));

        /* find connected components and add vertices to proper component graph*/
        int num_connected_components = boost::connected_components(input_graph, &component_map[0]);
        std::vector<simple_graph_t> components = std::vector<simple_graph_t>(num_connected_components);
        auto vertex_it = boost::vertices(input_graph);
        for (auto it = vertex_it.first; it != vertex_it.second; it++) {
            vertex_map[*it] = boost::add_vertex(components[component_map[*it]]);
        }

        /*for each edge in the original graph, add it to the proper component with updated edge labels*/
        auto edge_it = boost::edges(input_graph);
        for (auto it = edge_it.first; it != edge_it.second; it++) {
            int component_id = component_map[boost::source(*it, input_graph)];
            unsigned long source_id = vertex_map[boost::source(*it, input_graph)];
            unsigned long target_id = vertex_map[boost::target(*it, input_graph)];
            boost::add_edge(source_id, target_id, components[component_id]);
        }

        return components;
    }
};


#endif
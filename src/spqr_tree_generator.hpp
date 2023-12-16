#ifndef SPQR_TREE_GENERATOR_HPP
#define SPQR_TREE_GENERATOR_HPP

#include "spqr_tree.hpp"

namespace SPQRTreeGenerator {
    spqr_tree_t generate_spqr_tree(const basic_graph_t &input) {
        spqr_tree_t spqr_tree;
        //assert biconnected
        auto num_bicomponents = boost::biconnected_components(input, boost::dummy_property_map());
        if (num_bicomponents != 1) throw std::invalid_argument("SPQR Generator input must be biconnected!");


        return spqr_tree;
    }

    //decompose graph into simple graph
    std::pair<basic_graph_t, std::vector<spqr_vertex_t>> to_simple_graph(const basic_graph_t &input) {
        std::deque<basic_graph_t::edge_descriptor> new_edge_list(boost::edges(input).first, boost::edges(input).second);
        std::vector<std::deque<basic_graph_t::edge_descriptor>> buckets(boost::num_vertices(input));
        //radix sort by from vertex, then to vertex
        while (!new_edge_list.empty()) {
            basic_graph_t::edge_descriptor edge = new_edge_list.front();
            new_edge_list.pop_front();

            unsigned long from = boost::source(edge, input);
            unsigned long to = boost::target(edge, input);
            unsigned long lesser = std::min(from, to);
            buckets[lesser].push_back(edge);
        }
        for (std::deque<basic_graph_t::edge_descriptor> bucket: buckets) {
            while (!bucket.empty()) {
                new_edge_list.push_back(bucket.front());
                bucket.pop_front();
            }
        }
        while (!new_edge_list.empty()) {
            basic_graph_t::edge_descriptor edge = new_edge_list.front();
            new_edge_list.pop_front();

            unsigned long from = boost::source(edge, input);
            unsigned long to = boost::target(edge, input);
            unsigned long greater = std::max(from, to);
            buckets[greater].push_back(edge);
        }
        for (std::deque<basic_graph_t::edge_descriptor> bucket: buckets) {
            while (!bucket.empty()) {
                new_edge_list.push_back(bucket.front());
                bucket.pop_front();
            }
        }

        basic_graph_t simple_graph(boost::num_vertices(input));
        while (!new_edge_list.empty()) {
            basic_graph_t::edge_descriptor edge = new_edge_list.front();
            new_edge_list.pop_front();
            boost::add_edge(boost::source(edge, input), boost::target(edge, input), simple_graph);
        }
        return std::make_pair(simple_graph, std::vector<spqr_vertex_t>());
    }
}

#endif
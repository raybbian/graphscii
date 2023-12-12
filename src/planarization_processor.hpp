#ifndef PLANARIZATION_PROCESSOR_HPP
#define PLANARIZATION_PROCESSOR_HPP

#include <boost/graph/depth_first_search.hpp>
#include <boost/graph/connected_components.hpp>
#include "simple_graph.hpp"

namespace PlanarizationProcessor {
    simple_graph_t generate_dfs_spanning_tree(const simple_graph_t &input_graph) {
        simple_graph_t dfs_spanning_tree;

        /* make sure that the input graph is connected */
        int num_components = boost::connected_components(input_graph, boost::dummy_property_map());
        if (num_components != 1) throw std::invalid_argument("Planarization Processor input is not connected!");

        /* initialize our new tree */
        unsigned long num_vertices = input_graph.vertex_set().size();
        dfs_spanning_tree = simple_graph_t(num_vertices);

        /* initialize the visitor that adds gets the edges of the dfs spanning tree as a list */
        struct tree_edge_visitor : public boost::default_dfs_visitor {
            std::vector<simple_graph_t::edge_descriptor> &tree_edges;

            tree_edge_visitor(std::vector<simple_graph_t::edge_descriptor> &edges)
                    : tree_edges(edges) {}

            void tree_edge(simple_graph_t::edge_descriptor e, const simple_graph_t &g) {
                tree_edges.push_back(e);
            }
        };
        std::vector<simple_graph_t::edge_descriptor> spanning_tree_edges;
        tree_edge_visitor vis(spanning_tree_edges);

        /* run the dfs */
        boost::depth_first_search(input_graph, boost::visitor(vis));

        /* build the dfs_spanning_tree given these edges */
        for (const simple_graph_t::edge_descriptor &edge: spanning_tree_edges) {
            boost::add_edge(boost::source(edge, input_graph), boost::target(edge, input_graph), dfs_spanning_tree);
        }

        return dfs_spanning_tree;
    }
};

#endif
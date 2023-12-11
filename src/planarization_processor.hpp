#ifndef PLANARIZATION_PROCESSOR_HPP
#define PLANARIZATION_PROCESSOR_HPP

#include <boost/graph/depth_first_search.hpp>
#include <boost/graph/connected_components.hpp>
#include "simple_graph.hpp"
#include "planar_graph.hpp"

struct PlanarizationProcessor {
    SimpleGraph input_graph;
    SimpleGraph dfs_spanning_tree;
    PlanarGraph output_graph;

    PlanarizationProcessor(const SimpleGraph& input_graph) : input_graph(input_graph) {
        /* make sure that the input graph is connected */
        std::vector<int> components(boost::num_vertices(input_graph));
        int num_components = boost::connected_components(input_graph, &components[0]);
        if (num_components != 1) throw std::invalid_argument("Planarization Processor input is not connected!");

        unsigned long num_vertices = input_graph.vertex_set().size();
        dfs_spanning_tree = SimpleGraph(num_vertices);
    }

    void generate_dfs_spanning_tree() {
        /* initialize the visitor that adds gets the edges of the dfs spanning tree as a list */
        struct tree_edge_visitor : public boost::default_dfs_visitor {
            std::vector<boost::graph_traits<SimpleGraph>::edge_descriptor> &tree_edges;
            tree_edge_visitor(std::vector<boost::graph_traits<SimpleGraph>::edge_descriptor> &edges)
                    : tree_edges(edges) {}
            void tree_edge(boost::graph_traits<SimpleGraph>::edge_descriptor e, const SimpleGraph& g) {
                tree_edges.push_back(e);
            }
        };

        std::vector<boost::graph_traits<SimpleGraph>::edge_descriptor> spanning_tree_edges;
        tree_edge_visitor vis(spanning_tree_edges);

        /* run the dfs */
        boost::depth_first_search(input_graph, boost::visitor(vis));

        /* build the dfs_spanning_tree given these edges */
        for (const boost::graph_traits<SimpleGraph>::edge_descriptor& edge : spanning_tree_edges) {
            boost::add_edge(boost::source(edge, input_graph), boost::target(edge, input_graph), dfs_spanning_tree);
        }
    }
};

#endif
#ifndef BC_TREE_GENERATOR_HPP
#define BC_TREE_GENERATOR_HPP

#include <boost/graph/biconnected_components.hpp>
#include <boost/property_map/property_map.hpp>
#include <boost/graph/copy.hpp>
#include <boost/graph/graphviz.hpp>
#include "bc_tree.hpp"

namespace BCTreeGenerator {
    bc_tree_t generate_bc_tree(const simple_graph_t &input_graph) {
        struct BicomponentLabel {
            int bicomponent_id;
        };
        typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS, boost::no_property, BicomponentLabel> bicomponent_extractor;
        bicomponent_extractor copy_of_input_graph;
        bc_tree_t output;

        /* manually copy graph over to a graph with bicomponent label edge property - so that we can extract bicomponent IDs for each edge */
//        for (auto it = boost::vertices(input_graph); it.first != it.second; it.first++)
//            boost::add_vertex(copy_of_input_graph);
        for (auto it = boost::edges(input_graph); it.first != it.second; it.first++)
            boost::add_edge(boost::source(*it.first, input_graph), boost::target(*it.first, input_graph),
                            BicomponentLabel{-1}, copy_of_input_graph);

        /* generate the cutvertices and which blocks each edge belongs to in each graph */
        std::vector<int> articulation_points;
        auto bicomponent_map = boost::get(&BicomponentLabel::bicomponent_id, copy_of_input_graph);
        auto num_bicomponents = boost::biconnected_components(copy_of_input_graph, bicomponent_map,
                                                              std::back_inserter(articulation_points));

        /* iterating over edges, associate u and v with their corresponding blocks, and add the proper edges to each block */
        std::vector<std::unordered_map<unsigned long, unsigned long>> vertex_map(num_bicomponents.first);
        std::vector<simple_graph_t> blocks(num_bicomponents.first);
        for (auto it = boost::edges(copy_of_input_graph); it.first != it.second; it.first++) {
            unsigned long from_vertex = boost::source(*it.first, copy_of_input_graph);
            unsigned long to_vertex = boost::target(*it.first, copy_of_input_graph);
            int bicomponent_id = copy_of_input_graph[*it.first].bicomponent_id;
            if (!vertex_map[bicomponent_id].contains(from_vertex)) {
                vertex_map[bicomponent_id][from_vertex] = boost::add_vertex(blocks[bicomponent_id]);
            }
            if (!vertex_map[bicomponent_id].contains(to_vertex)) {
                vertex_map[bicomponent_id][to_vertex] = boost::add_vertex(blocks[bicomponent_id]);
            }
            boost::add_edge(vertex_map[bicomponent_id][from_vertex], vertex_map[bicomponent_id][to_vertex],
                            blocks[bicomponent_id]);
        }

        /* add these blocks as vertices into the BC tree - block[i] should correspond to vertex i in BC tree*/
        for (auto &block: blocks) {
            BCVertexProperty new_vertex{block_t, block};
            boost::add_vertex(new_vertex, output);
        }

        /* add the cutvertices as vertices into the BC tree */
        std::vector<int> is_cutvertex(boost::num_vertices(copy_of_input_graph),
                                      -1); //-1 if not, id of vertex in bc tree else
        for (int cutvertex: articulation_points) {
            simple_graph_t cutvertex_graph(1);
            BCVertexProperty new_vertex{cutvertex_t, cutvertex_graph};
            is_cutvertex[cutvertex] = boost::add_vertex(new_vertex, output);
        }

        /*for each edge, if it goes to or comes from a cutvertex, connect the corresponding block to the curvertex in the BC tree*/
        for (auto it = boost::edges(copy_of_input_graph); it.first != it.second; it.first++) {
            unsigned long from_vertex = boost::source(*it.first, copy_of_input_graph);
            unsigned long to_vertex = boost::target(*it.first, copy_of_input_graph);
            int bicomponent_id = copy_of_input_graph[*it.first].bicomponent_id;
            //if from vertex is cutvertex, connect block of edge to from vertex
            if (is_cutvertex[from_vertex] != -1 &&
                !boost::edge(is_cutvertex[from_vertex], bicomponent_id, output).second)
                boost::add_edge(is_cutvertex[from_vertex], bicomponent_id, output);
            if (is_cutvertex[to_vertex] != -1 &&
                !boost::edge(bicomponent_id, is_cutvertex[to_vertex], output).second)
                boost::add_edge(bicomponent_id, is_cutvertex[to_vertex], output);
        }
        return output;
    }
};

#endif
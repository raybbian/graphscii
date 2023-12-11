#ifndef BC_TREE_GENERATOR_HPP
#define BC_TREE_GENERATOR_HPP

#include <boost/graph/biconnected_components.hpp>
#include <boost/property_map/property_map.hpp>
#include <boost/graph/copy.hpp>

struct BCTreeGenerator {
    const simple_graph_t &input_graph; //non-const because need to modify edge property to display
    simple_graph_t copy_of_input_graph;
    std::vector<int> articulation_points;

    BCTreeGenerator(const simple_graph_t &input_graph) : input_graph(input_graph) {
        boost::copy_graph(input_graph, copy_of_input_graph);
    }

    void generate_bc_tree() {
        auto bicomponent_map = boost::get(&SimpleEdgeProperty::bicomponent_id, copy_of_input_graph);
        boost::biconnected_components(copy_of_input_graph, bicomponent_map, std::back_inserter(articulation_points));
    }
};

#endif
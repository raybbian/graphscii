#ifndef SPQR_TREE_GENERATOR_HPP
#define SPQR_TREE_GENERATOR_HPP

#include "spqr_tree.hpp"

namespace SPQRTreeGenerator {
    spqr_tree_t generate_spqr_tree(const simple_graph_t& input) {
        spqr_tree_t spqr_tree;
        //assert biconnected
        auto num_bicomponents = boost::biconnected_components(input, boost::dummy_property_map());
        if (num_bicomponents != 1) throw std::invalid_argument("SPQR Generator input must be biconnected!");

        return spqr_tree;
    }
}

#endif
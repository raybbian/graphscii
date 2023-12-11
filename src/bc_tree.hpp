#ifndef BC_TREE_HPP
#define BC_TREE_HPP

#include <boost/graph/adjacency_list.hpp>

struct BCVertexProperty {
    enum bc_vertex_t {
        block_t,
        cutvertex_t
    };
    simple_graph_t skeleton;
};

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS, BCVertexProperty> bc_tree_t;

#endif
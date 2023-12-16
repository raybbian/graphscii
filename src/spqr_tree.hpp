#ifndef SPQR_TREE_HPP
#define SPQR_TREE_HPP

#include <boost/graph/adjacency_list.hpp>

typedef enum {
    s_t,
    p_t,
    q_t,
    r_t,
} spqr_vertex_t;

struct SPQRVertexProperty {
    spqr_vertex_t type;
    basic_graph_t graph;
};

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS, SPQRVertexProperty> spqr_tree_t;

#endif
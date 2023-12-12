#ifndef BC_TREE_HPP
#define BC_TREE_HPP

#include <boost/graph/adjacency_list.hpp>

typedef enum {
    block_t,
    cutvertex_t
} bc_vertex_t;

struct BCVertexProperty {
    bc_vertex_t type;
    simple_graph_t skeleton;
};

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS, BCVertexProperty> bc_tree_t;

#endif
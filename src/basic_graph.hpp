#ifndef BASIC_GRAPH_HPP
#define BASIC_GRAPH_HPP

#include <boost/graph/adjacency_list.hpp>

struct BasicVertexProperty {
    unsigned long original_label;
};

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS, BasicVertexProperty>
        basic_graph_t;

#endif

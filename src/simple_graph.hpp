#ifndef SIMPLE_GRAPH_HPP
#define SIMPLE_GRAPH_HPP

#include <boost/graph/adjacency_list.hpp>

struct SimpleVertexProperty {

};

struct SimpleEdgeProperty {
    int bicomponent_id;
};

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS, SimpleVertexProperty, SimpleEdgeProperty> simple_graph_t;

#endif
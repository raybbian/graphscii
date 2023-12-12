#ifndef SIMPLE_GRAPH_HPP
#define SIMPLE_GRAPH_HPP

#include <boost/graph/adjacency_list.hpp>

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::undirectedS> simple_graph_t;

#endif
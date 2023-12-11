#ifndef SIMPLE_GRAPH_HPP
#define SIMPLE_GRAPH_HPP

#include <boost/graph/adjacency_list.hpp>

typedef boost::adjacency_list<boost::hash_setS, boost::vecS, boost::undirectedS, boost::no_property, boost::no_property, boost::hash_setS> SimpleGraph;

#endif
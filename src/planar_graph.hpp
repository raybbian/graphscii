#ifndef PLANAR_GRAPH_HPP
#define PLANAR_GRAPH_HPP

#include <boost/graph/adjacency_list.hpp>

enum PlanarGraphVertexT {
    crossing_dummy_t,
    vertex_t
};

struct planar_vertex_t {
    typedef boost::vertex_property_tag kind;
};

typedef boost::property<planar_vertex_t, PlanarGraphVertexT> PlanarVertexProperty;

typedef struct {
    boost::adjacency_list<boost::hash_setS, boost::vecS, boost::undirectedS, PlanarVertexProperty, boost::no_property, boost::hash_setS> backing_graph;
} PlanarGraph;


#endif
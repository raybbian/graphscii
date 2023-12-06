#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/depth_first_search.hpp>
#include <iostream>

struct name_t {
    typedef boost::vertex_property_tag kind;
};

struct age_t {
    typedef boost::vertex_property_tag kind;
};

typedef boost::property<name_t, std::string> WithName;
typedef boost::property<age_t, int, WithName> WithNameAndAge;
typedef boost::adjacency_list<boost::hash_setS, boost::vecS, boost::undirectedS, WithNameAndAge, boost::no_property, boost::hash_setS> MyGraphType;

struct tree_edge_visitor : public boost::default_dfs_visitor {
    std::vector<boost::graph_traits<MyGraphType>::edge_descriptor> &tree_edges;

    tree_edge_visitor(std::vector<boost::graph_traits<MyGraphType>::edge_descriptor> &edges)
            : tree_edges(edges) {}

    void tree_edge(boost::graph_traits<MyGraphType>::edge_descriptor e, const MyGraphType& g) {
        tree_edges.push_back(e);
    }
};


int main() {

    typedef std::pair<int, int> Pair;
    Pair edge_array[11] = {Pair(0, 1), Pair(0, 2), Pair(0, 3),
                           Pair(0, 4), Pair(1, 2), Pair(2, 3)};

    MyGraphType G(5);
    for (auto & i : edge_array)
        add_edge(i.first, i.second, G);

    boost::property_map<MyGraphType, name_t>::type name = boost::get(name_t(), G);
    boost::property_map<MyGraphType, age_t>::type age = boost::get(age_t(), G);
    boost::put(name, 0, "John");
    boost::put(age, 0, 19);
    boost::put(name, 1, "Katarina");
    boost::put(age, 0, 35);
    boost::put(name, 2, "Lux");
    boost::put(age, 0, 19);
    boost::put(name, 3, "Jarvan");
    boost::put(age, 0, 24);
    boost::put(name, 4, "Ahri");
    boost::put(age, 0, 99);

    auto iter_range = boost::adjacent_vertices(0, G);
    while(iter_range.first != iter_range.second) {
        std::string vertex_name = boost::get(name, *iter_range.first);
        std::cout << vertex_name << std::endl;
        iter_range.first++;
    }

    std::vector<boost::graph_traits<MyGraphType>::edge_descriptor> spanning_tree_edges;
    tree_edge_visitor vis(spanning_tree_edges);
    boost::depth_first_search(G, boost::visitor(vis));

    for (auto e : spanning_tree_edges) {
        std::cout << "Edge: " << source(e, G) << " - " << target(e, G) << std::endl;
    }
}

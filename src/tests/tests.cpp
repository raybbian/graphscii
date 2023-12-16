#include <boost/graph/graphviz.hpp>
#include <catch2/catch_test_macros.hpp>

#include "../basic_graph.hpp"
#include "../bc_tree_generator.hpp"
#include "../component_processor.hpp"
#include "../planarization_processor.hpp"
#include "../spqr_tree_generator.hpp"
#include "../spqr_tree_generator.hpp"
#include "../spqr_tree_generator.hpp"
#include "../spqr_tree_generator.hpp"
#include "../spqr_tree_generator.hpp"
#include "../spqr_tree_generator.hpp"
#include "../spqr_tree_generator.hpp"
#include "../spqr_tree_generator.hpp"
#include "../spqr_tree_generator.hpp"

TEST_CASE("generate dfs spanning tree") {
    basic_graph_t input(5);
    boost::add_edge(0, 1, input);
    boost::add_edge(0, 2, input);
    boost::add_edge(1, 2, input);
    boost::add_edge(2, 3, input);
    boost::add_edge(2, 4, input);
    boost::add_edge(3, 4, input);
    auto dfs_spanning_tree =
            PlanarizationProcessor::generate_dfs_spanning_tree(input);
    REQUIRE(boost::num_edges(dfs_spanning_tree) == 4);
    REQUIRE(boost::edge(0, 1, dfs_spanning_tree).second);
    REQUIRE(boost::edge(1, 2, dfs_spanning_tree).second);
    REQUIRE(boost::edge(2, 3, dfs_spanning_tree).second);
    REQUIRE(boost::edge(3, 4, dfs_spanning_tree).second);
    boost::write_graphviz(std::cout, dfs_spanning_tree);
}

TEST_CASE("throw on planarization of non-connected-graph") {
    basic_graph_t input;
    boost::add_edge(0, 1, input);
    boost::add_edge(1, 2, input);
    boost::add_edge(2, 0, input);
    boost::add_edge(3, 4, input);
    boost::add_edge(4, 5, input);
    boost::add_edge(5, 6, input);
    boost::add_edge(6, 3, input);
    CHECK_THROWS(PlanarizationProcessor::generate_dfs_spanning_tree(input));
}

TEST_CASE("decomposition into components") {
    basic_graph_t input;
    boost::add_edge(0, 1, input);
    boost::add_edge(1, 2, input);
    boost::add_edge(2, 0, input);
    boost::add_edge(3, 4, input);
    boost::add_edge(4, 5, input);
    boost::add_edge(5, 6, input);
    boost::add_edge(6, 3, input);
    auto components = ComponentProcessor::generate_connected_components(input);
    REQUIRE(components.size() == 2);
    REQUIRE(boost::edge(0, 1, components[0]).second);
    REQUIRE(boost::edge(1, 2, components[0]).second);
    REQUIRE(boost::edge(2, 0, components[0]).second);
    REQUIRE(boost::num_vertices(components[0]) == 3);
    REQUIRE(boost::edge(0, 1, components[1]).second);
    REQUIRE(boost::edge(1, 2, components[1]).second);
    REQUIRE(boost::edge(2, 3, components[1]).second);
    REQUIRE(boost::edge(3, 0, components[1]).second);
    REQUIRE(boost::num_vertices(components[1]) == 4);
    unsigned long vertex_count = 0;
    for (const auto &component: components) {
        vertex_count += boost::num_vertices(component);
    }
    REQUIRE(vertex_count == 7);
    for (auto &component: components) {
        boost::write_graphviz(std::cout, component);
    }
}

TEST_CASE("bc_tree identify cutvertices and blocks") {
    /*this is the graph from boost documentation*/
    basic_graph_t input(9);
    boost::add_edge(1, 2, input); // B C
    boost::add_edge(1, 3, input); // B D
    boost::add_edge(2, 3, input); // C D

    boost::add_edge(0, 1, input); // A B
    boost::add_edge(0, 5, input); // A F
    boost::add_edge(1, 4, input); // B E
    boost::add_edge(4, 5, input); // E F

    boost::add_edge(0, 6, input); // A G

    boost::add_edge(6, 7, input); // G H
    boost::add_edge(6, 8, input); // G I
    boost::add_edge(7, 8, input); // H I

    bc_tree_t bc_tree = BCTreeGenerator::generate_bc_tree(input);
    REQUIRE(boost::num_edges(bc_tree) == boost::num_vertices(bc_tree) - 1);

    boost::write_graphviz(std::cout, bc_tree);

    for (auto it = boost::vertices(bc_tree); it.first != it.second; it.first++) {
        std::cout << *it.first << " " << bc_tree[*it.first].type << std::endl;
        boost::write_graphviz(std::cout, bc_tree[*it.first].graph);
    }
}

TEST_CASE("spqr_tree step 1 test decompose into simple graph") {
    /*https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Multi-pseudograph.svg/330px-Multi-pseudograph.svg.png*/
    basic_graph_t input(6);
    boost::add_edge(0, 1, input);
    boost::add_edge(1, 2, input);
    boost::add_edge(2, 3, input);
    boost::add_edge(3, 4, input);
    boost::add_edge(4, 0, input);
    boost::add_edge(0, 4, input);
    boost::add_edge(0, 5, input);
    boost::add_edge(5, 5, input);
    boost::add_edge(0, 5, input);
    boost::add_edge(1, 5, input);
    boost::add_edge(2, 5, input);
    boost::add_edge(2, 5, input);
    boost::add_edge(3, 5, input);
    boost::add_edge(3, 5, input);
    boost::add_edge(4, 5, input);
    boost::add_edge(1, 1, input);
    boost::add_edge(2, 2, input);
    boost::add_edge(3, 3, input);

    basic_graph_t simple_graph = SPQRTreeGenerator::to_simple_graph(input).first;

    boost::write_graphviz(std::cout, simple_graph);
}
#include <boost/graph/adjacency_list.hpp>
#include <iostream>

using namespace boost;
using namespace std;

struct first_name_t {
    typedef vertex_property_tag kind;
};

template <class EdgeIter, class Graph>
void who_owes_who(EdgeIter first, EdgeIter last, const Graph& G) {
    // Access the propety acessor type for this graph
    constexpr first_name_t first_name{};
    typedef typename property_map<Graph,
            first_name_t>::const_type NameMap;
    NameMap name = get(first_name, G);

    typedef typename boost::property_traits<NameMap>
    ::value_type NameType;

    NameType src_name, targ_name;

    while (first != last) {
        src_name = boost::get(name, source(*first, G));
        targ_name = boost::get(name, target(*first, G));
        cout << src_name << " owes "
             << targ_name << " some money" << endl;
        ++first;
    }
}

int main() {
    typedef property<first_name_t, std::string> FirstNameProperty;
    typedef adjacency_list<vecS, vecS, directedS,
            FirstNameProperty> MyGraphType;

    typedef pair<int,int> Pair;
    Pair edge_array[11] = { Pair(0,1), Pair(0,2), Pair(0,3),
                            Pair(0,4), Pair(2,0), Pair(3,0),
                            Pair(2,4), Pair(3,1), Pair(3,4),
                            Pair(4,0), Pair(4,1) };

    MyGraphType G(5);
    for (int i = 0; i < 11; ++i)
        add_edge(edge_array[i].first, edge_array[i].second, G);

    property_map<MyGraphType, first_name_t>::type name = get(first_name_t(), G);

    boost::put(name, 0, "Jeremy");
    boost::put(name, 1, "Rich");
    boost::put(name, 2, "Andrew");
    boost::put(name, 3, "Jeff");
    name[4] = "Kinis"; // you can use operator[] too

    who_owes_who(edges(G).first, edges(G).second, G);
}

"""Deterministic synthetic policy workloads with disjoint entity ownership.

These are parameterized policy-cost microbenchmarks. They complement the
canonical 115-query suite; they do not claim to replay production IoT traffic.
"""
from dataclasses import asdict
from hashlib import sha256
from rdflib import Graph, Literal, Namespace, RDF, RDFS
from ..core import Query
from .campaign_config import Workload

NS = Namespace('urn:continuum:campaign:')


def build_workload(workload: Workload, seed: int, owner: int = 0, owners: int = 1) -> Graph:
    graph = Graph()
    graph.bind('bench', NS)
    # Every shard shares the schema. Data and all of its join paths have one owner.
    for kind in ('User', 'IoTDevice', 'Individual', 'Requirement', 'Policy'):
        graph.add((NS[kind], RDFS.subClassOf, NS.Record))
    index = 0
    for kind, count in [('User', workload.users), ('IoTDevice', workload.iot_devices),
                        ('Individual', workload.individuals), ('Requirement', workload.requirements),
                        ('Policy', workload.policies)]:
        for number in range(count):
            record = NS[f'{seed}-{kind}-{number}']
            if index % owners == owner:
                graph.add((record, RDF.type, NS[kind]))
                graph.add((record, NS.value, Literal(number)))
                current = record
                for level in range(workload.query_complexity):
                    nxt = NS[f'{seed}-{kind}-{number}-step-{level}']
                    graph.add((current, NS.next, nxt))
                    graph.add((nxt, NS.value, Literal(level)))
                    current = nxt
                # Policy count affects actual rule evaluation, not only metadata.
                for policy in range(workload.policies):
                    graph.add((record, NS[f'policy-{policy}'], Literal(True)))
            index += 1
    return graph


def query_for(workload: Workload, index: int, categories: tuple[str, ...]) -> Query:
    category = categories[index % len(categories)]
    # Query count generates distinct filters while retaining predictable nonempty bags.
    policy = index % workload.policies
    clauses = ['?record a bench:Record .', f'?record bench:policy-{policy} true .']
    previous = '?record'
    for level in range(workload.query_complexity):
        variable = f'?step{level}'
        clauses.append(f'{previous} bench:next {variable} .')
        previous = variable
    clauses.append(f'BIND({index} AS ?queryIndex)')
    text = 'PREFIX bench: <urn:continuum:campaign:> SELECT ?record ?queryIndex WHERE { ' + ' '.join(clauses) + ' }'
    return Query(f'policy-query-{index}', text, category, workload.query_complexity,
                 (f'policy-{policy}',))


def result_keys(graph: Graph, query: Query) -> list[str]:
    return sorted('\t'.join('' if term is None else term.n3() for term in row)
                  for row in graph.query(query.text))


def digest(keys) -> str:
    return sha256('\n'.join(sorted(keys)).encode()).hexdigest()

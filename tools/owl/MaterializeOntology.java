import java.io.File;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.formats.OWLXMLDocumentFormat;
import org.semanticweb.owlapi.formats.NTriplesDocumentFormat;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.*;
import org.semanticweb.owlapi.profiles.OWL2DLProfile;
import org.semanticweb.owlapi.io.RDFParserMetaData;

/** Named class/individual closure; see docs/design/PHYSICAL_REASONING.md. */
class MaterializeOntology {
    public static void main(String[] args) throws Exception {
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
        OWLOntology ontology = manager.loadOntologyFromOntologyDocument(new File(args[0]));
        OWLDataFactory df = manager.getOWLDataFactory();
        // OWLAPI 4 returns metadata/Set directly; OWLAPI 5 uses Optional/Stream.
        Object metadata = manager.getOntologyFormat(ontology).getOntologyLoaderMetaData();
        if (metadata instanceof java.util.Optional)
            metadata = ((java.util.Optional<?>) metadata).orElse(null);
        if (metadata instanceof RDFParserMetaData) {
            Object remaining = ((RDFParserMetaData) metadata).getUnparsedTriples();
            boolean unparsed = remaining instanceof java.util.Collection
                ? !((java.util.Collection<?>) remaining).isEmpty()
                : ((java.util.stream.Stream<?>) remaining).findAny().isPresent();
            if (unparsed) throw new IllegalArgumentException("Unsupported RDF-to-OWL mapping: unparsed triples remain");
        }
        // RDF serializations commonly omit declarations; add only declarations
        // of entities already recognized by OWLAPI before structural validation.
        for (OWLEntity entity : ontology.getSignature())
            manager.addAxiom(ontology, df.getOWLDeclarationAxiom(entity));
        String violations = new OWL2DLProfile().checkOntology(ontology).toString();
        if (!new OWL2DLProfile().checkOntology(ontology).isInProfile())
            throw new IllegalArgumentException("Unsupported OWL 2 DL input: " + violations);
        if (args[2].equals("convert")) {
            if (!ontology.getAxioms(AxiomType.HAS_KEY).isEmpty())
                throw new IllegalArgumentException("Konclude does not support HasKey axioms");
            manager.saveOntology(ontology, new OWLXMLDocumentFormat(), IRI.create(new File(args[1])));
            return;
        }
        OWLReasonerFactory factory = (OWLReasonerFactory) Class.forName(args[2]).getDeclaredConstructor().newInstance();
        OWLReasoner reasoner = factory.createReasoner(ontology);
        try {
            if (!reasoner.isConsistent()) {
                System.err.println("CONTINUUM_INCONSISTENT");
                System.exit(3);
            }
            OWLOntology output = manager.createOntology();
            for (OWLClass cls : ontology.getClassesInSignature()) {
                for (OWLClass sup : reasoner.getSuperClasses(cls, false).getFlattened())
                    manager.addAxiom(output, df.getOWLSubClassOfAxiom(cls, sup));
                for (OWLClass eq : reasoner.getEquivalentClasses(cls).getEntities()) {
                    manager.addAxiom(output, df.getOWLSubClassOfAxiom(cls, eq));
                    if (!eq.equals(cls)) manager.addAxiom(output, df.getOWLEquivalentClassesAxiom(cls, eq));
                }
            }
            for (OWLNamedIndividual individual : ontology.getIndividualsInSignature()) {
                for (OWLClass cls : reasoner.getTypes(individual, false).getFlattened())
                    manager.addAxiom(output, df.getOWLClassAssertionAxiom(cls, individual));
                for (OWLNamedIndividual same : reasoner.getSameIndividuals(individual).getEntities())
                    if (!same.equals(individual)) manager.addAxiom(output, df.getOWLSameIndividualAxiom(individual, same));
            }
            manager.saveOntology(output, new NTriplesDocumentFormat(), IRI.create(new File(args[1])));
            System.out.println("CONTINUUM_MATERIALIZED");
        } finally { reasoner.dispose(); }
    }
}

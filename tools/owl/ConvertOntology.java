import java.io.File;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.formats.OWLXMLDocumentFormat;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyManager;

/** Convert any OWLAPI-readable serialization to Konclude-native OWL/XML. */
public final class ConvertOntology {
    private ConvertOntology() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            throw new IllegalArgumentException("usage: ConvertOntology INPUT OUTPUT");
        }
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
        OWLOntology ontology = manager.loadOntologyFromOntologyDocument(
            new File(args[0])
        );
        manager.saveOntology(
            ontology,
            new OWLXMLDocumentFormat(),
            IRI.create(new File(args[1]))
        );
    }
}

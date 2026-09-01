import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.stream.Collectors;
import org.semanticweb.HermiT.ReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.profiles.OWL2DLProfile;
import org.semanticweb.owlapi.profiles.OWLProfileReport;
import org.semanticweb.owlapi.reasoner.OWLReasoner;

/** Optional OWLAPI/HermiT check; no changes to the loaded ontology. */
class CheckOntology {
    private static String quote(String value) {
        StringBuilder result = new StringBuilder("\"");
        for (int index = 0; index < value.length(); index++) {
            char c = value.charAt(index);
            if (c == '"' || c == '\\') {
                result.append('\\').append(c);
            } else if (c < 0x20) {
                result.append(String.format("\\u%04x", (int) c));
            } else {
                result.append(c);
            }
        }
        return result.append('"').toString();
    }

    public static void main(String[] args) throws Exception {
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
        OWLOntology ontology = manager.loadOntologyFromOntologyDocument(new File(args[0]));
        OWLProfileReport profile = new OWL2DLProfile().checkOntology(ontology);
        Map<String, Integer> violations = new TreeMap<>();
        profile.getViolations().forEach(violation ->
            violations.merge(violation.getClass().getSimpleName(), 1, Integer::sum));
        OWLReasoner reasoner = new ReasonerFactory().createReasoner(ontology);
        boolean consistent;
        List<String> unsatisfiable = new ArrayList<>();
        try {
            consistent = reasoner.isConsistent();
            if (consistent) {
                reasoner.getUnsatisfiableClasses().getEntitiesMinusBottom().forEach(
                    entity -> unsatisfiable.add(entity.getIRI().toString()));
            }
            unsatisfiable.sort(String::compareTo);
            String violationJson = violations.entrySet().stream()
                .map(entry -> quote(entry.getKey()) + ":" + entry.getValue())
                .collect(Collectors.joining(",", "{", "}"));
            String classesJson = unsatisfiable.stream().map(CheckOntology::quote)
                .collect(Collectors.joining(",", "[", "]"));
            String examplesJson = profile.getViolations().stream().map(Object::toString)
                .sorted().limit(5).map(CheckOntology::quote)
                .collect(Collectors.joining(",", "[", "]"));
            System.out.println("CONTINUUM_OWL_REPORT\t{" +
                "\"reasoner\":" + quote(reasoner.getReasonerName()) +
                ",\"reasoner_version\":" + quote(reasoner.getReasonerVersion().toString()) +
                ",\"axioms\":" + ontology.getAxiomCount() +
                ",\"consistent\":" + consistent +
                ",\"unsatisfiable_classes\":" + classesJson +
                ",\"owl2_dl_profile\":" + profile.isInProfile() +
                ",\"profile_violation_count\":" + profile.getViolations().size() +
                ",\"profile_violation_types\":" + violationJson +
                ",\"profile_violation_examples\":" + examplesJson + "}");
        } finally {
            reasoner.dispose();
        }
        if (!consistent || !unsatisfiable.isEmpty()) {
            System.exit(1);
        }
    }
}

# Import concrete rule modules to trigger registration hooks with RuleRegistry on load
import app.domains.optimization.rules.compute
import app.domains.optimization.rules.storage
import app.domains.optimization.rules.database
import app.domains.optimization.rules.networking
import app.domains.optimization.rules.kubernetes
import app.domains.optimization.rules.finops
import app.domains.optimization.rules.security
import app.domains.optimization.rules.sustainability

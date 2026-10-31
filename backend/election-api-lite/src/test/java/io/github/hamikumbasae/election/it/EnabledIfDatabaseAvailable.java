package io.github.hamikumbasae.election.it;

import org.junit.jupiter.api.extension.ConditionEvaluationResult;
import org.junit.jupiter.api.extension.ExecutionCondition;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.extension.ExtensionContext;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.net.InetSocketAddress;
import java.net.Socket;

/**
 * Runs the annotated tests only when the real {@code secim} database is reachable and a password is given
 * (DB_HOST, default 127.0.0.1; DB_PORT, default 3306; DB_PASSWORD). Otherwise they are reported as skipped,
 * so {@code mvn verify} stays green on machines and CI runners without the data.
 */
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@ExtendWith(EnabledIfDatabaseAvailable.Condition.class)
public @interface EnabledIfDatabaseAvailable {

    class Condition implements ExecutionCondition {
        @Override
        public ConditionEvaluationResult evaluateExecutionCondition(ExtensionContext context) {
            String host = env("DB_HOST", "127.0.0.1");
            int port = Integer.parseInt(env("DB_PORT", "3306"));
            if (System.getenv("DB_PASSWORD") == null) {
                return ConditionEvaluationResult.disabled("DB_PASSWORD not set; skipping database integration tests");
            }
            try (Socket socket = new Socket()) {
                socket.connect(new InetSocketAddress(host, port), 1_000);
                return ConditionEvaluationResult.enabled("MariaDB reachable at " + host + ":" + port);
            } catch (Exception e) {
                return ConditionEvaluationResult.disabled("MariaDB not reachable at " + host + ":" + port);
            }
        }

        private static String env(String name, String fallback) {
            String v = System.getenv(name);
            return v == null || v.isBlank() ? fallback : v;
        }
    }
}

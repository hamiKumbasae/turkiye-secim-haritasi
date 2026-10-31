package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.service.BadRequestException;
import io.github.hamikumbasae.election.service.NotFoundException;
import jakarta.validation.ConstraintViolationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.method.ParameterValidationResult;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import java.net.URI;
import java.util.stream.Collectors;

/**
 * Every error is an RFC 9457 problem detail ({@code application/problem+json}). The base class already maps
 * Spring MVC's own exceptions (missing/mistyped parameters, failed {@code @Min}/{@code @Pattern} checks on
 * handler arguments, unknown routes) to 400/404/405.
 */
@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /** Lists every failed constraint, e.g. "plate: must be less than or equal to 81". */
    @Override
    protected ResponseEntity<Object> handleHandlerMethodValidationException(HandlerMethodValidationException ex,
            HttpHeaders headers, HttpStatusCode status, WebRequest request) {
        String detail = ex.getParameterValidationResults().stream()
                .flatMap(r -> r.getResolvableErrors().stream().map(e -> parameterName(r) + ": " + e.getDefaultMessage()))
                .collect(Collectors.joining("; "));
        ProblemDetail body = problem(HttpStatus.BAD_REQUEST, "Bad request", detail.isEmpty() ? "Validation failure" : detail);
        return handleExceptionInternal(ex, body, headers, HttpStatus.BAD_REQUEST, request);
    }

    private static String parameterName(ParameterValidationResult r) {
        String name = r.getMethodParameter().getParameterName();
        return name == null ? "argument " + r.getMethodParameter().getParameterIndex() : name;
    }

    @ExceptionHandler(NotFoundException.class)
    ProblemDetail notFound(NotFoundException e) {
        return problem(HttpStatus.NOT_FOUND, "Not found", e.getMessage());
    }

    @ExceptionHandler({BadRequestException.class, IllegalArgumentException.class, ConstraintViolationException.class})
    ProblemDetail badRequest(RuntimeException e) {
        return problem(HttpStatus.BAD_REQUEST, "Bad request", e.getMessage());
    }

    @ExceptionHandler(DataAccessException.class)
    ProblemDetail database(DataAccessException e) {
        log.error("Database error", e);
        return problem(HttpStatus.SERVICE_UNAVAILABLE, "Database unavailable",
                "The election database could not be queried. Check the DB connection and try again.");
    }

    private static ProblemDetail problem(HttpStatus status, String title, String detail) {
        ProblemDetail p = ProblemDetail.forStatusAndDetail(status, detail);
        p.setTitle(title);
        p.setType(URI.create("about:blank"));
        return p;
    }
}

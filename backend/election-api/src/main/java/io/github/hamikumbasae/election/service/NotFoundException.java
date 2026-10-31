package io.github.hamikumbasae.election.service;

/** Mapped to HTTP 404 by the global exception handler. */
public class NotFoundException extends RuntimeException {
    public NotFoundException(String message) {
        super(message);
    }
}

package io.github.hamikumbasae.election.service;

/** Mapped to HTTP 400 by the global exception handler. */
public class BadRequestException extends RuntimeException {
    public BadRequestException(String message) {
        super(message);
    }
}

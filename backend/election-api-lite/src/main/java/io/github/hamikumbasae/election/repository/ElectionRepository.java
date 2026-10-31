package io.github.hamikumbasae.election.repository;

import io.github.hamikumbasae.election.domain.Election;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ElectionRepository extends JpaRepository<Election, Integer> {
}

package com.example.erp.repository;

import com.example.erp.entity.Part;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface PartRepository extends JpaRepository<Part, Long> {

    List<Part> findByNameContainingIgnoreCase(String name);

    List<Part> findBySupplierId(Long supplierId);

    @Query("SELECT p FROM Part p WHERE " +
           "(:name IS NULL OR p.name LIKE %:name%) AND " +
           "(:category IS NULL OR p.category = :category) AND " +
           "(:supplierId IS NULL OR p.supplierId = :supplierId)")
    Page<Part> search(@Param("name") String name,
                      @Param("category") String category,
                      @Param("supplierId") Long supplierId,
                      Pageable pageable);
}

package com.example.erp.repository;

import com.example.erp.entity.Supplier;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface SupplierRepository extends JpaRepository<Supplier, Long> {

    List<Supplier> findByNameContainingIgnoreCase(String name);

    @Query("SELECT s FROM Supplier s WHERE " +
           "(:name IS NULL OR s.name LIKE %:name%) AND " +
           "(:status IS NULL OR s.status = :status) AND " +
           "(:creditRating IS NULL OR s.creditRating = :creditRating)")
    Page<Supplier> search(@Param("name") String name,
                          @Param("status") Integer status,
                          @Param("creditRating") String creditRating,
                          Pageable pageable);
}

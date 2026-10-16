package com.example.erp.repository;

import com.example.erp.entity.Inventory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface InventoryRepository extends JpaRepository<Inventory, Long> {

    Optional<Inventory> findByPartId(Long partId);

    @Query("SELECT i FROM Inventory i WHERE i.currentQuantity < i.safetyStock")
    List<Inventory> findWarnings();

    @Query("SELECT i FROM Inventory i JOIN Part p ON i.partId = p.id WHERE " +
           "(:partName IS NULL OR p.name LIKE %:partName%) AND " +
           "(:warehouseLocation IS NULL OR i.warehouseLocation LIKE %:warehouseLocation%)")
    Page<Inventory> search(@Param("partName") String partName,
                          @Param("warehouseLocation") String warehouseLocation,
                          Pageable pageable);
}

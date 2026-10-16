package com.example.erp.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "part")
public class Part {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String partCode;

    @Column(nullable = false)
    private String name;

    private String model;
    private String specification;
    private String unit;

    private Double purchasePrice;
    private Double suggestedRetailPrice;

    /** 安全库存阈值（低于此值触发预警） */
    private Integer stockWarningValue;

    private Long supplierId;
    private String category;
    @Column(length = 1000)
    private String description;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getPartCode() { return partCode; }
    public void setPartCode(String partCode) { this.partCode = partCode; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getModel() { return model; }
    public void setModel(String model) { this.model = model; }
    public String getSpecification() { return specification; }
    public void setSpecification(String specification) { this.specification = specification; }
    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }
    public Double getPurchasePrice() { return purchasePrice; }
    public void setPurchasePrice(Double purchasePrice) { this.purchasePrice = purchasePrice; }
    public Double getSuggestedRetailPrice() { return suggestedRetailPrice; }
    public void setSuggestedRetailPrice(Double suggestedRetailPrice) { this.suggestedRetailPrice = suggestedRetailPrice; }
    public Integer getStockWarningValue() { return stockWarningValue; }
    public void setStockWarningValue(Integer stockWarningValue) { this.stockWarningValue = stockWarningValue; }
    public Long getSupplierId() { return supplierId; }
    public void setSupplierId(Long supplierId) { this.supplierId = supplierId; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
}

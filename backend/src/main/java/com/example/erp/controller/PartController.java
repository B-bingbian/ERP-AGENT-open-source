package com.example.erp.controller;

import com.example.erp.common.BadRequestException;
import com.example.erp.common.PageResult;
import com.example.erp.common.R;
import com.example.erp.common.NotFoundException;
import com.example.erp.entity.Inventory;
import com.example.erp.entity.Part;
import com.example.erp.repository.InventoryRepository;
import com.example.erp.repository.PartRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/parts")
public class PartController {

    private final PartRepository repo;
    private final InventoryRepository inventoryRepo;

    public PartController(PartRepository repo, InventoryRepository inventoryRepo) {
        this.repo = repo;
        this.inventoryRepo = inventoryRepo;
    }

    @GetMapping("/get/{id}")
    public Part get(@PathVariable Long id) {
        return repo.findById(id)
                .orElseThrow(() -> new NotFoundException("零部件不存在: id=" + id));
    }

    @GetMapping("/search")
    public List<Part> search(@RequestParam String name) {
        return repo.findByNameContainingIgnoreCase(name);
    }

    @GetMapping("/supplier/{supplierId}")
    public List<Part> bySupplier(@PathVariable Long supplierId) {
        return repo.findBySupplierId(supplierId);
    }

    @GetMapping("/page")
    public PageResult<Part> page(@RequestParam(defaultValue = "1") int current,
                                @RequestParam(defaultValue = "10") int size,
                                @RequestParam(required = false) String name,
                                @RequestParam(required = false) String category,
                                @RequestParam(required = false) Long supplierId) {
        Page<Part> p = repo.search(name, category, supplierId, PageRequest.of(current - 1, size));
        return new PageResult<>(p.getContent(), p.getTotalElements(), current, size);
    }

    @PostMapping("/create")
    public R<Part> create(@RequestBody Part body) {
        if (body.getPartCode() == null || body.getName() == null || body.getPurchasePrice() == null) {
            throw new BadRequestException("partCode / name / purchasePrice 为必填");
        }
        Part saved = repo.save(body);
        // 自动建一条库存记录
        Inventory inv = new Inventory();
        inv.setPartId(saved.getId());
        inv.setCurrentQuantity(0);
        inv.setSafetyStock(saved.getStockWarningValue() == null ? 10 : saved.getStockWarningValue());
        inv.setWarehouseLocation("主仓-A区");
        inventoryRepo.save(inv);
        return R.ok(saved);
    }
}

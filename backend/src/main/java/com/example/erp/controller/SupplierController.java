package com.example.erp.controller;

import com.example.erp.common.BadRequestException;
import com.example.erp.common.PageResult;
import com.example.erp.common.R;
import com.example.erp.common.NotFoundException;
import com.example.erp.entity.Supplier;
import com.example.erp.repository.SupplierRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/suppliers")
public class SupplierController {

    private final SupplierRepository repo;
    public SupplierController(SupplierRepository repo) { this.repo = repo; }

    @GetMapping("/search")
    public List<Supplier> search(@RequestParam String name) {
        return repo.findByNameContainingIgnoreCase(name);
    }

    @GetMapping("/page")
    public PageResult<Supplier> page(@RequestParam(defaultValue = "1") int current,
                                     @RequestParam(defaultValue = "10") int size,
                                     @RequestParam(required = false) String name,
                                     @RequestParam(required = false) Integer status,
                                     @RequestParam(required = false) String creditRating) {
        Page<Supplier> p = repo.search(name, status, creditRating, PageRequest.of(current - 1, size));
        return new PageResult<>(p.getContent(), p.getTotalElements(), current, size);
    }

    @GetMapping("/get/{id}")
    public Supplier get(@PathVariable Long id) {
        return repo.findById(id)
                .orElseThrow(() -> new NotFoundException("供应商不存在: id=" + id));
    }

    @PostMapping("/create")
    public R<Supplier> create(@RequestBody Supplier body) {
        if (body.getSupplierCode() == null || body.getName() == null) {
            throw new BadRequestException("supplierCode 和 name 为必填");
        }
        return R.ok(repo.save(body));
    }

    @PatchMapping("/update-status/{id}")
    public R<Supplier> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        Supplier s = repo.findById(id)
                .orElseThrow(() -> new NotFoundException("供应商不存在: id=" + id));
        s.setStatus(status);
        return R.ok(repo.save(s));
    }
}

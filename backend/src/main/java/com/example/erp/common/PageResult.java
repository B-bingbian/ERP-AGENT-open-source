package com.example.erp.common;

import java.util.List;

/**
 * 统一分页返回结构。字段名与 MCP 工具注释约定一致：records/total/current/size/pages。
 */
public class PageResult<T> {
    private List<T> records;
    private long total;
    private int current;
    private int size;
    private int pages;

    public PageResult() {}

    public PageResult(List<T> records, long total, int current, int size) {
        this.records = records;
        this.total = total;
        this.current = current;
        this.size = size;
        this.pages = size == 0 ? 0 : (int) Math.ceil((double) total / size);
    }

    public List<T> getRecords() { return records; }
    public void setRecords(List<T> records) { this.records = records; }
    public long getTotal() { return total; }
    public void setTotal(long total) { this.total = total; }
    public int getCurrent() { return current; }
    public void setCurrent(int current) { this.current = current; }
    public int getSize() { return size; }
    public void setSize(int size) { this.size = size; }
    public int getPages() { return pages; }
    public void setPages(int pages) { this.pages = pages; }
}

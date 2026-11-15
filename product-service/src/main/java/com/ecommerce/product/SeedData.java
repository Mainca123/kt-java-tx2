package com.ecommerce.product;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

@Component @ConditionalOnProperty(name="app.seed-data",havingValue="true",matchIfMissing=true)
public class SeedData implements CommandLineRunner {
    private final JdbcTemplate jdbc;
    public SeedData(JdbcTemplate jdbc) { this.jdbc=jdbc; }
    @Override public void run(String... args) {
        // Fixed demo IDs and INSERT IGNORE make seeding safe when two replicas start together.
        jdbc.update("INSERT IGNORE INTO products (id,name,price,stock,version) VALUES (1,'Laptop Java Developer',15000000.00,20,0),(2,'Ban phim co',850000.00,50,0),(3,'Chuot khong day',250000.00,100,0)");
    }
}

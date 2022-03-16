package com.tpcstld.twozerogame;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.util.Arrays;

public class Tile extends Cell {
    private final int value;
    @Nullable
    private Tile[] mergedFrom = null;

    public Tile(int x, int y, int value) {
        super(x, y);
        this.value = value;
    }

    public Tile(Cell cell, int value) {
        super(cell.getX(), cell.getY());
        this.value = value;
    }

    public void updatePosition(Cell cell) {
        this.setX(cell.getX());
        this.setY(cell.getY());
    }

    public int getValue() {
        return this.value;
    }

    public Tile[] getMergedFrom() {
        return mergedFrom;
    }

    public void setMergedFrom(Tile[] tile) {
        mergedFrom = tile;
    }

    @NonNull
    @Override
    public String toString() {
        return Tile.class.getSimpleName() + "{" +
                "value=" + value +
                ", mergedFrom=" + Arrays.toString(mergedFrom) +
                '}';
    }
}

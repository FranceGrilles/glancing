#! /bin/sh

for i in 1 5 10 25 50 75 100 200 300 400 500 750 1000; do
  [ -f "random_${i}M.bin" ] || dd if=/dev/urandom of="random_${i}M.bin" bs=1M count=${i};
done

if [ ! -f random_1M_gz.bin.gz ]; then
  cp -f random_1M.bin random_1M_gz.bin
  gzip random_1M_gz.bin
fi
rm -f random_1M_gz.bin

if [ ! -f random_1M_bz2.bin.bz2 ]; then
  cp -f random_1M.bin random_1M_bz2.bin
  bzip2 random_1M_bz2.bin
fi
rm -f random_1M_bz2.bin

if [ ! -f random_1M_zip.bin.zip ]; then
  cp -f random_1M.bin random_1M_zip.bin
  zip random_1M_zip.bin.zip random_1M_zip.bin
fi
rm -f random_1M_zip.bin

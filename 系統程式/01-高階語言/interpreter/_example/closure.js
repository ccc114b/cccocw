function createCounter() {
    let count = 0; // 這個變數被下面的內層函式「捕獲」了
    return function() {
        count++; // 這裡使用了外部變數
        return count;
    };
}

const counter = createCounter(); // createCounter 執行結束
console.log(counter()); // 1，它依然記得 count
console.log(counter()); // 2，依然記得 count
console.log(counter()); // 3，依然記得 count
console.log(counter()); // 4，依然記得 count
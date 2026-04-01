(defun is-divisible (n d)
  (if (< n d)
      0
      (if (= n d)
          1
          (is-divisible (- n d) d))))

(defun divisor-test (n divisor)
  (if (= n divisor)
      1
      (if (= (is-divisible n divisor) 1)
          0
          (divisor-test n (+ divisor 1)))))

(defun is-prime (n)
  (if (< n 2)
      (print 0)
      (if (= (divisor-test n 2) 1)
          (print 1)
          (print 0))))

(is-prime 19)
(is-prime 21)
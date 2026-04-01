(defun sum-to-n (n)
  (if (= n 0)
      0
      (+ n (sum-to-n (- n 1)))))

(print (sum-to-n 10))
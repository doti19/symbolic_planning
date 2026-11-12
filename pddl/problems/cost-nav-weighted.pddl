
(define (problem cost-navigation-weighted)

    (:domain building)

    (:objects
        entrance hallway office lab meeting - room
    )

    (:init
        (robot-at entrance)

        ;; Building connections
        (connected entrance hallway)
        (connected hallway entrance)

        (connected hallway office)
        (connected office hallway)

        (connected office meeting)
        (connected meeting office)

        (connected entrance lab)
        (connected lab entrance)

        (connected lab meeting)
        (connected meeting lab)

        ;; Initialize total cost
        (= (total-cost) 0)

        ;; Short route, expensive
        (= (distance entrance lab) 8)
        (= (distance lab entrance) 8)

        (= (distance lab meeting) 7)
        (= (distance meeting lab) 7)

        ;; Longer route, cheaper
        (= (distance entrance hallway) 3)
        (= (distance hallway entrance) 3)

        (= (distance hallway office) 3)
        (= (distance office hallway) 3)

        (= (distance office meeting) 3)
        (= (distance meeting office) 3)
    )

    (:goal
        (robot-at meeting)
    )

    (:metric minimize (total-cost))
)

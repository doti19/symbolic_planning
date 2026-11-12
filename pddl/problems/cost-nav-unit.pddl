
(define (problem cost-navigation-unit)

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
        (= (distance entrance lab) 1)
        (= (distance lab entrance) 1)

        (= (distance lab meeting) 1)
        (= (distance meeting lab) 1)

        ;; Longer route, cheaper
        (= (distance entrance hallway) 1)
        (= (distance hallway entrance) 1)

        (= (distance hallway office) 1)
        (= (distance office hallway) 1)

        (= (distance office meeting) 1)
        (= (distance meeting office) 1)
    )

    (:goal
        (robot-at meeting)
    )

    (:metric minimize (total-cost))
)

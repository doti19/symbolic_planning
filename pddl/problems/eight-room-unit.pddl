
(define (problem eight-room-unit)

  (:domain building)

  (:objects
    entrance hallway office lab meeting
    library classroom storage - room
  )

  (:init
    ;; Robot starts at the entrance
    (robot-at entrance)

    ;; Original five-room connections
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

    ;; New connections
    (connected hallway library)
    (connected library hallway)

    (connected library classroom)
    (connected classroom library)

    (connected classroom storage)
    (connected storage classroom)

    (connected storage meeting)
    (connected meeting storage)

    ;; Initialize total cost
    (= (total-cost) 0)

    ;; Original travel costs
    (= (distance entrance hallway) 1)
    (= (distance hallway entrance) 1)

    (= (distance hallway office) 1)
    (= (distance office hallway) 1)

    (= (distance office meeting) 1)
    (= (distance meeting office) 1)

    (= (distance entrance lab) 1)
    (= (distance lab entrance) 1)

    (= (distance lab meeting) 1)
    (= (distance meeting lab) 1)

    ;; New travel costs
    (= (distance hallway library) 1)
    (= (distance library hallway) 1)

    (= (distance library classroom) 1)
    (= (distance classroom library) 1)

    (= (distance classroom storage) 1)
    (= (distance storage classroom) 1)

    (= (distance storage meeting) 1)
    (= (distance meeting storage) 1)
  )

  ;; Navigate to the new Storage room
  (:goal
    (robot-at storage)
  )

  (:metric minimize (total-cost))
)

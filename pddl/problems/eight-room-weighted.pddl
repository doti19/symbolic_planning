
(define (problem eight-room-weighted)

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
    (= (distance entrance hallway) 3)
    (= (distance hallway entrance) 3)

    (= (distance hallway office) 3)
    (= (distance office hallway) 3)

    (= (distance office meeting) 3)
    (= (distance meeting office) 3)

    (= (distance entrance lab) 8)
    (= (distance lab entrance) 8)

    (= (distance lab meeting) 7)
    (= (distance meeting lab) 7)

    ;; New travel costs
    (= (distance hallway library) 2)
    (= (distance library hallway) 2)

    (= (distance library classroom) 2)
    (= (distance classroom library) 2)

    (= (distance classroom storage) 2)
    (= (distance storage classroom) 2)

    (= (distance storage meeting) 3)
    (= (distance meeting storage) 3)
  )

  ;; Navigate to the new Storage room
  (:goal
    (robot-at storage)
  )

  (:metric minimize (total-cost))
)

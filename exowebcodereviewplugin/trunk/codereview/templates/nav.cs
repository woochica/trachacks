<div id="ctxtnav" class="nav">
  <h2>CodeReview Navigation</h2>
  <ul>
      <li class="first">
          <?cs if:main == "yes" ?>CodeReviewsMain
          <?cs else ?><a href="<?cs var:main.href ?>">CodeReviewsMain</a>
          <?cs /if ?>
      </li>
      <li>
          <?cs if:completed == "yes" ?>CompletelyReviewed
          <?cs else ?><a href="<?cs var:completed.href ?>">CompletelyReviewed</a>
          <?cs /if ?>
      </li>
      <li class="last">
          <?cs if:manager=="yes" ?>CodeReviewManager
          <?cs else ?><a href="<?cs var:manager.href ?>">CodeReviewManager</a>
          <?cs /if ?>
      </li>
  </ul>
</div>
